"""비동기 유틸리티"""

import asyncio
import functools


def to_async(func):
    """
    동기 함수를 비동기적으로 실행할 수 있도록 하는 데코레이터입니다.
    내부적으로 asyncio.to_thread를 사용하여 별도의 스레드에서 함수를 실행합니다.
    Python 3.9 이상에서 사용 가능합니다.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # asyncio.to_thread를 사용하여 동기 함수를 별도의 스레드에서 실행합니다.
        # functools.partial을 사용하여 함수의 인자를 전달합니다.
        return await asyncio.to_thread(functools.partial(func, *args, **kwargs))

    return wrapper
