from dotenv import load_dotenv
from pytest import fixture


@fixture(autouse=True, scope="session")
def load_test_env():
    load_dotenv("tests/.env", override=False)
