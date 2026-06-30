document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');
  
  const statsNodes = document.getElementById('stats-nodes');
  const statsEdges = document.getElementById('stats-edges');
  const statsGaps = document.getElementById('stats-gaps');
  const statsCoverage = document.getElementById('stats-coverage');
  
  const nodeSelector = document.getElementById('node-selector');
  const graphIframe = document.getElementById('graph-iframe');
  const resetBtn = document.getElementById('reset-graph-btn');
  
  const egoIndicator = document.getElementById('ego-indicator');
  const egoNodeName = document.getElementById('ego-node-name');
  const clearEgoBtn = document.getElementById('clear-ego-btn');
  
  const complianceList = document.getElementById('compliance-list');
  const failuresList = document.getElementById('failures-list');

  // Tab Switching
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      // Deactivate current tabs
      tabButtons.forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      tabPanes.forEach(p => p.classList.remove('active'));
      
      // Activate clicked tab
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      const paneId = btn.getAttribute('aria-controls');
      document.getElementById(paneId).classList.add('active');
    });
  });

  // Load General Dashboard Stats
  async function loadStats() {
    try {
      const res = await fetch('/api/stats');
      const stats = await res.json();
      
      statsNodes.textContent = stats.node_count;
      statsEdges.textContent = stats.edge_count;
      statsGaps.textContent = stats.nodes_by_type.REGULATION ? Object.keys(stats.orphaned_nodes).length : '0';
      statsCoverage.textContent = `${stats.equipment_coverage_pct}%`;
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  }

  // Load Compliance Gaps
  async function loadComplianceGaps() {
    try {
      const res = await fetch('/api/compliance-gaps?date=2025-09-01');
      const gaps = await res.json();
      
      // Update top counter
      statsGaps.textContent = gaps.length;
      
      if (gaps.length === 0) {
        complianceList.innerHTML = `<p style="color: var(--success); font-weight: 500;">✓ All active equipment compliant with regulations.</p>`;
        return;
      }
      
      complianceList.innerHTML = gaps.map(gap => `
        <div class="gap-card">
          <div class="gap-header">
            <span class="gap-title">⚠️ ${gap.equipment_id} Compliance Warning</span>
            <span class="gap-tag">${gap.regulation_id}</span>
          </div>
          <div class="gap-details">
            <div><strong>Asset Type:</strong> ${gap.equipment_type}</div>
            <div><strong>Authority:</strong> ${gap.authority}</div>
            <div><strong>Last Inspection:</strong> ${gap.last_inspection}</div>
            <div><strong>Status:</strong> Overdue</div>
          </div>
          <div class="gap-reason">
            ${gap.reason}
          </div>
        </div>
      `).join('');
    } catch (err) {
      console.error('Error loading compliance gaps:', err);
      complianceList.innerHTML = `<p style="color: var(--danger);">Failed to load compliance records.</p>`;
    }
  }

  // Load Failure Patterns
  async function loadFailurePatterns() {
    try {
      const res = await fetch('/api/failure-patterns');
      const patterns = await res.json();
      
      if (patterns.length === 0) {
        failuresList.innerHTML = `<p style="color: var(--success); font-weight: 500;">✓ No recurring failure patterns detected in recent maintenance records.</p>`;
        return;
      }
      
      failuresList.innerHTML = patterns.map(pat => {
        const oemContent = pat.recommendations.map(rec => `
          <div class="oem-block">
            <div class="oem-title">OEM Instruction Reference: ${rec.section}</div>
            <p>${rec.recommendation}</p>
          </div>
        `).join('') || '<p style="color: var(--text-muted); font-size: 0.85rem;">No direct OEM manual recommendation links found in graph.</p>';

        return `
          <div class="failure-card">
            <div class="failure-header">
              <span class="failure-title">⚡ Recurring ${pat.failure_type}</span>
              <span class="failure-count">${pat.count} Failures</span>
            </div>
            <p style="font-size: 0.9rem; margin-bottom: 0.5rem;">
              Asset <strong>${pat.equipment_id}</strong> (${pat.equipment_type}) has exceeded the failure frequency threshold.
            </p>
            ${oemContent}
          </div>
        `;
      }).join('');
    } catch (err) {
      console.error('Error loading failure patterns:', err);
      failuresList.innerHTML = `<p style="color: var(--danger);">Failed to load failure risk analysis.</p>`;
    }
  }

  // Populate Node Dropdown Selector for Focus Mode
  async function populateNodeSelector() {
    try {
      const res = await fetch('/api/nodes');
      const nodes = await res.json();
      
      // Filter key nodes (like Equipment, Regulations) to avoid populating trivial dates
      const keyNodes = nodes.filter(n => ['EQUIPMENT', 'REGULATION', 'FAILURE_MODE'].includes(n.label));
      
      // Sort alphabetically
      keyNodes.sort((a, b) => a.id.localeCompare(b.id));
      
      keyNodes.forEach(node => {
        const opt = document.createElement('option');
        opt.value = node.id;
        opt.textContent = `${node.id} (${node.label})`;
        nodeSelector.appendChild(opt);
      });
    } catch (err) {
      console.error('Error populating node selector:', err);
    }
  }

  // Handle Graph Focus Navigation
  function focusOnNode(nodeId) {
    if (!nodeId) {
      resetGraph();
      return;
    }
    
    // Update iframe source to focused ego-network
    graphIframe.src = `/api/graph-viz?node_id=${encodeURIComponent(nodeId)}`;
    
    // Show focus badge
    egoNodeName.textContent = nodeId;
    egoIndicator.style.display = 'block';
    nodeSelector.value = nodeId;
  }

  function resetGraph() {
    graphIframe.src = '/api/graph-viz';
    egoIndicator.style.display = 'none';
    nodeSelector.value = '';
  }

  // Event Listeners
  nodeSelector.addEventListener('change', (e) => {
    focusOnNode(e.target.value);
  });
  
  resetBtn.addEventListener('click', resetGraph);
  clearEgoBtn.addEventListener('click', resetGraph);

  // Initialize page
  loadStats();
  loadComplianceGaps();
  loadFailurePatterns();
  populateNodeSelector();
});
