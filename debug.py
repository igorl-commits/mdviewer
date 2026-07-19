"""Debug logging for mdviewer. Leaf module — no app imports (avoids cycles)."""
import logging
import os

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
