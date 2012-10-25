import logging
import warnings

fmt_string = '%(name)-16s: %(levelname)-8s %(message)s'
logging.basicConfig(filename="log/log", filemode='a',
                    level=logging.INFO,
                    format=fmt_string)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter(fmt_string))
logging.getLogger('').addHandler(console)
logging.captureWarnings(True)
warnings.formatwarning = lambda *args: re.sub("\n", "", args[0].message.strip())