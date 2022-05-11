from dataclasses import dataclass

@dataclass
class DB:
    server: str
    port: int
    user: str 
    password: str


@dataclass
class Params:
    a: int
    b: int 

@dataclass
class Config:
    db: DB
    params: Params