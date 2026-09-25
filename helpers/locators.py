from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

OWN_TEXT_JS = """
(el) => {
  const direct = Array.from(el.childNodes)
    .filter(n => n.nodeType === 3)
    .map(n => n.textContent)
    .join(' ');
  const star = Array.from(el.children)
    .filter(c => c.tagName === 'SPAN' && c.textContent.trim() === '*')
    .map(c => c.textContent)
    .join(' ');
  return (direct + ' ' + star).replace(/\\*/g, ' ').replace(/\\s+/g, ' ').trim();
}
"""

FIND_LABEL_JS = """
(root, names) => {
  const normalize = (t) => (t || '').toLowerCase().replace(/\\*/g, ' ').replace(/\\s+/g, ' ').trim();
  const wanted = new Set(names.map(normalize));
  const ownText = (el) => {
    const direct = Array.from(el.childNodes)
      .filter(n => n.nodeType === 3)
      .map(n => n.textContent)
      .join(' ');
    const star = Array.from(el.children)
      .filter(c => c.tagName === 'SPAN' && c.textContent.trim() === '*')
      .map(c => c.textContent)
      .join(' ');
    return (direct + ' ' + star).replace(/\\*/g, ' ').replace(/\\s+/g, ' ').trim();
  };
  let best = null;
  let bestLen = Infinity;
  for (const el of root.querySelectorAll('*')) {
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') continue;
    if (el.offsetWidth === 0 && el.offsetHeight === 0) continue;
    if (!wanted.has(normalize(ownText(el)))) continue;
    const size = (el.outerHTML || '').length;
    if (size < bestLen) {
      best = el;
      bestLen = size;
    }
  }
  return best;
}
"""


class LocatorHelpers:
    def first_visible(self, locator, timeout=5000):
        try:
            locator.first.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeoutError:
            return None
        count = locator.count()
        for i in range(count):
            el = locator.nth(i)
            if el.is_visible():
                return el
        return None

    def child_visible(self, el, selector, timeout=500):
        """Visible child of a Locator or ElementHandle."""
        if hasattr(el, "locator"):
            return self.first_visible(el.locator(selector), timeout=timeout)
        handle = el.query_selector(selector)
        if handle is not None and handle.is_visible():
            return handle
        return None

    def own_text(self, el):
        return el.evaluate(OWN_TEXT_JS)

    def find_exact_label(self, root, names):
        handle = root.evaluate_handle(FIND_LABEL_JS, list(names))
        return handle.as_element()
