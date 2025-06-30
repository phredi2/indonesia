import os
import asyncio
import json
import base64
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

try:
    import aiohttp
except ImportError as exc:  # pragma: no cover - better message if deps missing
    raise SystemExit("Missing dependency 'aiohttp'. Install with 'pip install aiohttp'") from exc

try:
    from solana.rpc.async_api import AsyncClient
    from solana.transaction import Transaction
    from solana.keypair import Keypair
except ImportError as exc:
    raise SystemExit(
        "Missing dependency 'solana'. Install with 'pip install solana'"
    ) from exc

# Token mints
SOL_MINT = "So11111111111111111111111111111111111111112"
USDC_MINT = "EPjFWdd5AufqSSqeM2qWVCN4zpwoS9E8oqecGbp6vK"  # USDC on Solana

DEXS = ["Raydium", "Lifinity", "Orca", "Meteora", "Jupiter"]
JUPITER_URL = os.getenv("JUPITER_API_URL", "https://quote-api.jup.ag")
RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
PROFIT_THRESHOLD = float(os.getenv("PROFIT_THRESHOLD", 0.0005))  # 0.05%
SLIPPAGE_LIMIT = float(os.getenv("SLIPPAGE_LIMIT", 0.005))
TRADE_AMOUNT = int(os.getenv("TRADE_AMOUNT", 100_000_000))  # lamports (0.1 SOL)

@dataclass
class RouteCheckResult:
    pair: str
    dex_buy: str
    dex_sell: str
    expected_input: int
    expected_output: int
    profit: int
    reason: str

class JupiterClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.session = session

    async def get_quote(self, input_mint: str, output_mint: str, amount: int, dex: str) -> Optional[Dict[str, Any]]:
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "swapMode": "ExactIn",
            "onlyDirectRoutes": "true",
            "dexes": dex,
        }
        async with self.session.get(f"{JUPITER_URL}/v6/quote", params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            routes = data.get("data") or []
            return routes[0] if routes else None

class ArbitrageBot:
    PAIR = "SOL/USDC"

    def __init__(self) -> None:
        self.keypair: Optional[Keypair] = None
        kp_path = os.getenv("KEYPAIR_PATH")
        if kp_path and os.path.exists(kp_path):
            with open(kp_path, "r") as fh:
                secret = json.load(fh)
            self.keypair = Keypair.from_secret_key(bytes(secret))
        self.client: Optional[AsyncClient] = None

    async def scan_once(self, session: aiohttp.ClientSession) -> List[RouteCheckResult]:
        results: List[RouteCheckResult] = []
        jup = JupiterClient(session)
        quotes: Dict[str, Dict[str, Optional[Dict[str, Any]]]] = {}
        for dex in DEXS:
            buy = await jup.get_quote(USDC_MINT, SOL_MINT, TRADE_AMOUNT, dex)
            sell = await jup.get_quote(SOL_MINT, USDC_MINT, TRADE_AMOUNT, dex)
            quotes[dex] = {"buy": buy, "sell": sell}
        for buy_dex in DEXS:
            for sell_dex in DEXS:
                if buy_dex == sell_dex:
                    continue
                buy = quotes[buy_dex]["buy"]
                sell = quotes[sell_dex]["sell"]
                if not buy or not sell:
                    results.append(RouteCheckResult(self.PAIR, buy_dex, sell_dex, TRADE_AMOUNT, 0, 0, "no route"))
                    continue
                input_amt = int(buy.get("inAmount", TRADE_AMOUNT))
                output_amt = int(sell.get("outAmount", 0))
                profit = output_amt - input_amt
                reason = ""
                if profit <= input_amt * PROFIT_THRESHOLD:
                    reason = "profit below threshold"
                if reason:
                    results.append(RouteCheckResult(self.PAIR, buy_dex, sell_dex, input_amt, output_amt, profit, reason))
                    continue
                # placeholder for slippage, liquidity checks
                results.append(RouteCheckResult(self.PAIR, buy_dex, sell_dex, input_amt, output_amt, profit, "trade executed"))
        return results

    async def execute_swap(self, encoded_tx: str) -> None:
        if not self.keypair or not self.client:
            print("Wallet or RPC client not configured; cannot execute trade.")
            return
        tx_bytes = base64.b64decode(encoded_tx)
        tx = Transaction.deserialize(tx_bytes)
        tx.sign(self.keypair)
        await self.client.send_transaction(tx, self.keypair)

    async def run(self) -> None:
        async with AsyncClient(RPC_URL) as client, aiohttp.ClientSession() as session:
            self.client = client
            while True:
                results = await self.scan_once(session)
                for r in results:
                    print(r)
                await asyncio.sleep(5)

if __name__ == "__main__":
    bot = ArbitrageBot()
    asyncio.run(bot.run())
