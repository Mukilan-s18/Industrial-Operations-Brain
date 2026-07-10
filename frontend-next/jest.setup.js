import '@testing-library/jest-dom'
import { TextEncoder, TextDecoder } from 'util';
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

window.HTMLElement.prototype.scrollIntoView = function() {};
