"""Debug logging for mdviewer. Leaf module — no app imports (avoids cycles)."""
import logging
import os
import time

_DEBUG = os.environ.get('MDVIEWER_DEBUG') == '1'
if _DEBUG:
    _log_dir = os.path.join(os.environ.get('APPDATA', ''), 'mdviewer')
    os.makedirs(_log_dir, exist_ok=True)
    _log_path = os.path.join(_log_dir, 'debug.log')
    logging.basicConfig(
        filename=_log_path,
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(message)s',
        filemode='w',
    )
    logging.info('mdviewer starting, argv logging enabled')


def _dlog(msg, *args):
    if _DEBUG:
        logging.debug(msg, *args)


def _diag(msg, *args):
    """Diagnostics log for drag/debugging, enabled only when MDVIEWER_DEBUG=1.
    Writes to APPDATA/mdviewer/debug-diag.log. Kept separate from the standard
    logging so it can be added/removed without touching the logging setup.
    """
    if not _DEBUG:
        return
    try:
        log_path = os.path.join(os.environ.get('APPDATA', ''), 'mdviewer', 'debug-diag.log')
        line = (msg % args if args else msg)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write('%s %s\n' % (time.strftime('%H:%M:%S'), line))
    except Exception:
        pass
