import datetime
from sc4py.env import env_as_bool


SHOW_SUPPORT_FORM = env_as_bool("SHOW_SUPPORT_FORM", True)
SHOW_SUPPORT_CHAT = env_as_bool("SHOW_SUPPORT_CHAT", True)

PROJECT_COMPANY = "IFRN"
PROJECT_TITLE = "Integrador AVA"
PROJECT_SUBTITLE = "Sistema de integração de Ambientes Virtuais de Aprendizagem"
PROJECT_VERSION = "local-dev"
PROJECT_LAST_STARTUP = int(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)
PROJECT_COPYRIGHT = "@2025 PROJECT_COPYRIGHT"
PROJECT_LICENSE = "Licença MIT"
PROJECT_LICENSE_URL = "https://opensource.org/license/mit"
