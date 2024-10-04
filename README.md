# Overview
### Runner With API
A seamless bridge between long-running asynchronous tasks and a modern HTTP API using FastAPI or Litestar.

This library makes it easy to build interactive services that couple a continuous background process with an HTTP server. By integrating FastAPI and Litestar, we are leveraging the familiar programming style of decorated path operation functions that can interact directly with the processing loop, enabling dynamic configuration and monitoring through HTTP endpoints.

### Why is this powerful?
Traditional Python services often separate long-running background processes and API servers, forcing you to use cumbersome intermediaries like message brokers or polling. Runner With API sidesteps these complications by keeping everything within the same process. The API can directly interact with internal states of the long-running task, making operations like runtime configuration, monitoring, or pausing the runner straightforward and highly efficient.

Using Runner With API, it's easier than ever to manage complex, persistent tasks — like robotics controllers, data processors, or IoT devices — directly from a convenient HTTP interface.

# Installation
- `pip install git+https://github.com/dorinclisu/runner-with-api.git@<version-tag>`
- Check available [tags](https://github.com/dorinclisu/runner-with-api/tags) for \<version-tag>


# Usage
### Litestar
```python
# example.py
import logging

from anyio import sleep
from litestar import Litestar, get, put
from runner_with_api import AsyncRunnerWithAPI


class MyRunner(AsyncRunnerWithAPI):
    def __init__(self):
        ...

    async def init(self):
        logging.info('Initializing process ...')
        await sleep(1)
        self.config = {}

    async def run(self) -> None:
        logging.info('Running ...')
        while True:
            await sleep(1)

    @put('/config')
    async def configure(self, data: dict) -> None:
        logging.info('Configuring process')
        self.config = data

    @get('/config')
    async def get_config(self) -> dict:
        return self.config


runner = MyRunner()

api = Litestar(runner.litestar_handlers(),
    lifespan=[runner.lifespan]
)

if __name__ == '__main__':
    runner.run_with_api(api)
    # or just run from cli: $ uvicorn example:api

```
See `tests/test_litestar.py` for more details.

### FastAPI
See `tests/test_fastapi.py` for more details.
