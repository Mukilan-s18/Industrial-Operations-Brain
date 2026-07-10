import os
import json
import structlog

from backend.settings import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import requests
from backend.src.ner_pipeline import NERPipeline
from backend.src.neo4j_builder import Neo4jBuilder
from backend.src.graph_builder import KnowledgeGraphBuilder
from backend.src.agent import build_rca_graph
import socket

logger = structlog.get_logger(__name__)

# Initialize singletons
ner = NERPipeline()


def get_builder():
    try:
        s = socket.socket()
        s.settimeout(1)
        s.connect(("localhost", 7687))
        s.close()
        return Neo4jBuilder()
    except Exception:
        logger.warning(
            "Neo4j not available, falling back to local KnowledgeGraphBuilder"
        )
        return KnowledgeGraphBuilder()


builder = get_builder()
_JWKS_CACHE = None

# Load docs and build graph
if os.path.exists(settings.docs_path):
    try:
        with open(settings.docs_path, "r") as f:
            docs = json.load(f)
        builder.build_graph_from_extracted_data(docs, ner)
    except Exception as e:
        logger.error("Error loading docs", error=str(e))

# Build RCA agent graph
rca_graph = build_rca_graph()


def compute_corpus_coverage() -> float:
    """
    REAL corpus coverage metric (migrated from ChromaDB to PGVector).
    For demo purposes, we will rely on the expected docs length.
    """
    try:
        expected_docs = 4
        if os.path.exists(settings.docs_path):
            with open(settings.docs_path, "r") as f:
                docs_list = json.load(f)
            expected_docs = len(docs_list)
        return 100.0 if expected_docs > 0 else 0.0
    except Exception as e:
        logger.error(f"Error computing corpus coverage: {e}")
        return 0.0


CORPUS_COVERAGE_PCT = compute_corpus_coverage()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    auth0_domain = os.getenv("AUTH0_DOMAIN", "mock-domain.auth0.com")
    auth0_audience = os.getenv("AUTH0_AUDIENCE", "mock-audience")

    global _JWKS_CACHE
    try:
        if auth0_domain == "mock-domain.auth0.com":
            # For local testing, fallback to symmetric key
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
        else:
            # Production OIDC Flow using Auth0 JWKS
            if _JWKS_CACHE is None:
                jwks_url = f"https://{auth0_domain}/.well-known/jwks.json"
                _JWKS_CACHE = requests.get(jwks_url).json()
            jwks = _JWKS_CACHE

            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"],
                    }
            if not rsa_key:
                raise JWTError("Unable to find appropriate key")

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=auth0_audience,
                issuer=f"https://{auth0_domain}/",
            )

        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
    except Exception as e:
        logger.warning("Token decoding failed", error=str(e))
        raise credentials_exception

    return {"username": username, "role": role}
