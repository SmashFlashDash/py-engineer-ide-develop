'''Импорт зависимостей ИВК'''
import sys, os, inspect
sys.path.insert(0, os.getcwd() + "/lib")
from cpi_framework.utils.basecpi_abc import *
from ivk import config
from ivk.log_db import DbLog
from cpi_framework.spacecrafts.omka.cpi import CPIBASE
from cpi_framework.spacecrafts.omka.cpi import CPICMD
from cpi_framework.spacecrafts.omka.cpi import CPIKC
from cpi_framework.spacecrafts.omka.cpi import CPIMD
from cpi_framework.spacecrafts.omka.cpi import CPIPZ
from cpi_framework.spacecrafts.omka.cpi import CPIRIK
from cpi_framework.spacecrafts.omka.cpi import OBTS
from ivk.scOMKA.simplifications import SCPICMD
from cpi_framework.spacecrafts.omka.otc import OTC
from ivk.scOMKA.simplifications import SOTC
from ivk.scOMKA.controll_kpa import KPA
from ivk.scOMKA.simplifications import SKPA
from ivk.scOMKA.controll_iccell import ICCELL
from ivk.scOMKA.simplifications import SICCELL
from ivk.scOMKA.controll_scpi import SCPI
Ex = config.get_exchange()
from time import sleep
