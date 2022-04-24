FROM --platform=linux/x86_64 python:3

WORKDIR /home

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

RUN tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib \
    && ./configure \
    && make \
    && make install

RUN pip install ta-lib

ENV LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"
EXPOSE 5001

CMD [ "python", "./run.py" ]

