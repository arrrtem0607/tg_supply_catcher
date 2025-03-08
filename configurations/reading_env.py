from environs import Env

env: Env = Env()
# env.read_env(path="/home/ff_bot/ff_bot/.env")
env.read_env(path=".env")
