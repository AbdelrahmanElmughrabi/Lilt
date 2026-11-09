export type FileItem = { id: string; title: string; kind: 'document' | 'recording'; source?: string | null; state?: string };
export type FileMenu = { item: FileItem; x: number; y: number; anchor: HTMLElement };
export type OpenFileMenu = (menu: FileMenu) => void;

// An action lets buttons and recording cards share the same pointer/keyboard behavior.
export function fileContext(node: HTMLElement, options: { item: FileItem | null; open: OpenFileMenu }) {
  function open(event: MouseEvent | KeyboardEvent) {
    if (!options.item) return;
    event.preventDefault();
    event.stopPropagation();
    const rect = node.getBoundingClientRect();
    const pointer = event instanceof MouseEvent && (event.clientX !== 0 || event.clientY !== 0);
    options.open({ item: options.item, anchor: node,
      x: pointer ? event.clientX : rect.left + 12, y: pointer ? event.clientY : rect.bottom });
  }
  function keydown(event: KeyboardEvent) {
    if (event.key === 'ContextMenu' || (event.shiftKey && event.key === 'F10')) open(event);
  }
  const originalTabindex = node.getAttribute('tabindex');
  function updateTabindex() {
    if (node.tagName !== 'BUTTON' && originalTabindex === null) {
      if (options.item) node.tabIndex = 0;
      else node.removeAttribute('tabindex');
    }
  }
  updateTabindex();
  node.addEventListener('contextmenu', open);
  node.addEventListener('keydown', keydown);
  return {
    update(next: typeof options) { options = next; updateTabindex(); },
    destroy() {
      node.removeEventListener('contextmenu', open);
      node.removeEventListener('keydown', keydown);
      if (originalTabindex === null && node.tagName !== 'BUTTON') node.removeAttribute('tabindex');
    },
  };
}
