import logging
import argparse

import telegram.ext as tg_ext

from bot import handlers
import client

import data.db_session

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, required=True)
    return parser.parse_args()


def main() -> None:
    data.db_session.global_init('db/main.sqlite')

    args = parse_args()
    application = tg_ext.Application.builder().token(args.token).build()
    session = client.SearchSession()
    handlers.setup_handlers(application, session)

    application.run_polling()


if __name__ == "__main__":
    main()
