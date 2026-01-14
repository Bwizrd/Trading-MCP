import json

with open('symbols.json', 'r') as f:
    symbols = json.load(f)

# Currently collecting ticks for:
# 205 NAS100
# 220 US500
# 217 UK100
# 200 GER40
# 219 US30

indices = []
metals = []
crypto = []

for s in symbols:
    name = s.get('symbolName', '')
    desc = s.get('description', '').lower()
    sid = s.get('symbolId')
    
    # Skip if not enabled
    if not s.get('enabled', False):
        continue
    
    # Look for major indices (similar to US500, NAS100)
    if any(x in name.upper() for x in ['JP225', 'EUR50', 'FRA40', 'SPA35', 'ITA40', 'SUI20', 'AUS200', 'HK50', 'CHI50', 'NLD25']):
        indices.append({'id': sid, 'name': name, 'desc': s.get('description')})
    
    # Gold and Silver
    if 'XAU' in name or 'gold' in desc:
        metals.append({'id': sid, 'name': name, 'desc': s.get('description')})
    if 'XAG' in name or 'silver' in desc:
        metals.append({'id': sid, 'name': name, 'desc': s.get('description')})
    
    # Bitcoin and major crypto
    if 'BTC' in name.upper() or 'bitcoin' in desc:
        crypto.append({'id': sid, 'name': name, 'desc': s.get('description')})

print('='*80)
print('RECOMMENDED SYMBOLS FOR BULK BACKTEST')
print('='*80)

print('\n===== MAJOR INDICES (Similar behavior to US500/NAS100) =====')
for idx in sorted(indices, key=lambda x: x['name']):
    print(f'{idx["id"]:4d} | {idx["name"]:25s} | {idx["desc"]}')

print('\n===== GOLD & SILVER (Trend-following potential) =====')
for m in sorted(metals, key=lambda x: x['name']):
    print(f'{m["id"]:4d} | {m["name"]:25s} | {m["desc"]}')

print('\n===== BITCOIN & CRYPTO (High volatility) =====')
for c in sorted(crypto, key=lambda x: x['name']):
    print(f'{c["id"]:4d} | {c["name"]:25s} | {c["desc"]}')

print('\n' + '='*80)
print('SUMMARY FOR BULK BACKTEST')
print('='*80)

all_candidates = indices + metals + crypto
print(f'\nTotal candidates: {len(all_candidates)}')
print(f'  - Indices: {len(indices)}')
print(f'  - Metals:  {len(metals)}')
print(f'  - Crypto:  {len(crypto)}')

print('\nRecommended symbols for testing:')
print('  Indices: JP225_SB, EUR50_SB, FRA40_SB, AUS200_SB')
print('  Metals:  XAUUSD_SB (Gold), XAGUSD_SB (Silver)')
print('  Crypto:  BTCUSD_SB')

print('\nSymbol IDs for bulk_backtest:')
symbol_ids = [s['id'] for s in all_candidates]
print(f'symbols = {sorted(symbol_ids)}')
