from lib_common.logger.configs import loggers
from lib_common.cryptor.configs import cryptors
from lib_common.connect.configs import databases

run_logger = loggers.get_logger("run")
dt_cryptor = cryptors.get_cryptor("default")
app_db = databases.get_database("app")
local_db = databases.get_database("local")

if __name__ == "__main__":
    run_logger.info(f"xxxx")