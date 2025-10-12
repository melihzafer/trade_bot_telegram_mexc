"""
Pydantic models for trading data structures.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


Side = Literal["BUY", "SELL"]
OrderStatus = Literal["OPEN", "CLOSED", "CANCELED"]


class Signal(BaseModel):
    """Raw signal parsed from Telegram message."""
    
    source: str = Field(description="Telegram channel username or ID")
    ts: datetime = Field(description="Signal timestamp")
    symbol: str = Field(description="Trading pair e.g., BTCUSDT")
    side: Side = Field(description="BUY or SELL")
    entry: Optional[float] = Field(default=None, description="Entry price")
    sl: Optional[float] = Field(default=None, description="Stop loss price")
    tp: Optional[float] = Field(default=None, description="Take profit price")
    note: Optional[str] = Field(default=None, description="Original message snippet")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Order(BaseModel):
    """Paper trade order representation."""
    
    id: str = Field(description="Unique order ID")
    signal_id: str = Field(description="Source signal identifier")
    symbol: str = Field(description="Trading pair")
    side: Side = Field(description="BUY or SELL")
    qty: float = Field(description="Order quantity in base asset")
    entry_price: float = Field(description="Entry price")
    sl: Optional[float] = Field(default=None, description="Stop loss price")
    tp: Optional[float] = Field(default=None, description="Take profit price")
    opened_at: datetime = Field(description="Order open timestamp")
    closed_at: Optional[datetime] = Field(default=None, description="Order close timestamp")
    status: OrderStatus = Field(default="OPEN", description="Order status")
    pnl_usdt: float = Field(default=0.0, description="Realized PnL in USDT")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Candle(BaseModel):
    """OHLCV candle data."""
    
    ts: int = Field(description="Timestamp in milliseconds")
    open: float = Field(description="Open price")
    high: float = Field(description="High price")
    low: float = Field(description="Low price")
    close: float = Field(description="Close price")
    volume: float = Field(description="Volume")

    @classmethod
    def from_ccxt(cls, data: list) -> "Candle":
        """Create Candle from ccxt OHLCV array [ts, o, h, l, c, v]."""
        return cls(
            ts=data[0],
            open=data[1],
            high=data[2],
            low=data[3],
            close=data[4],
            volume=data[5],
        )


class BacktestResult(BaseModel):
    """Result of a backtest run for a single signal."""
    
    signal: Signal
    outcome: Literal["WIN", "LOSS", "OPEN", "ERROR"] = Field(description="Trade outcome")
    entry_price: Optional[float] = Field(default=None)
    exit_price: Optional[float] = Field(default=None)
    pnl_pct: Optional[float] = Field(default=None, description="P&L percentage")
    bars_held: Optional[int] = Field(default=None, description="Number of candles held")
    error_msg: Optional[str] = Field(default=None, description="Error message if any")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
