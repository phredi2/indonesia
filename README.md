# Solana Arbitrage Bot

This project implements a minimal Python bot that scans decentralized exchanges (DEXs) on Solana for potential arbitrage routes. It uses the [Jupiter](https://jup.ag) quote API to fetch prices from multiple venues and can optionally execute profitable trades if a keypair is provided.

Supported DEXs:

- [Raydium](https://raydium.io)
- [Lifinity](https://lifinity.io)
- [Orca](https://www.orca.so)
- [Meteora](https://www.meteora.ag)
- [Jupiter](https://jup.ag)

> **Warning**
> Running an automated trading bot on mainnet is risky. Ensure you fully understand the code and supply your own wallet and RPC configuration before executing any trades.

## Requirements

- Python 3.10+
- `aiohttp` and `solana` Python packages

Install dependencies:

```bash
pip install aiohttp solana
```

If you run the bot without these packages installed it will exit with an
informative message.

## Configuration

Several environment variables control runtime behaviour:

- `SOLANA_RPC_URL` – RPC endpoint (defaults to `https://api.mainnet-beta.solana.com`)
- `JUPITER_API_URL` – base URL for Jupiter quotes (`https://quote-api.jup.ag` by default)
- `KEYPAIR_PATH` – path to a JSON-encoded Solana keypair for signing trades (optional)
- `PROFIT_THRESHOLD` – minimum profit ratio before executing a swap (default `0.0005`)
- `SLIPPAGE_LIMIT` – slippage tolerance when executing swaps (default `0.005`)
- `TRADE_AMOUNT` – amount of SOL (in lamports) used when quoting trades (default `100000000`)

## Running

```bash
python src/bot.py
```

The bot will continuously request quotes from Jupiter, compare buy/sell prices across DEXs and print the results. If you provide a keypair it will attempt to sign and submit swaps for routes that exceed the profit threshold.

Because the bot relies on network access, execution inside a restricted environment may fail.
