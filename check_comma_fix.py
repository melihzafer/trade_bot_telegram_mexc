from parsers.enhanced_parser import EnhancedParser

parser = EnhancedParser()

# Just count the critical tests
tests_fixed = []
tests_still_broken = []

# Test #9: Comma decimal (0,125)
text9 = "DOGE long giriş 0,125 hedef 0,130 - 0,135 stop 0,120 15x"
result9 = parser.parse(text9)
if result9.entries == [0.125] and 0.13 in result9.tps and 0.135 in result9.tps:
    tests_fixed.append(9)
else:
    tests_still_broken.append((9, f"entries={result9.entries}, tps={result9.tps}"))

# Test #4: Comma with k (112,5k)
text4 = "SOL LONG giriş 112,5k hedef 114,2k stop 110k kaldıraç 15x"
result4 = parser.parse(text4)
if result4.entries == [112500.0] and result4.tps == [114200.0]:
    tests_fixed.append(4)
else:
    tests_still_broken.append((4, f"entries={result4.entries}, tps={result4.tps}"))

# Test #17: Comma decimal (0.085)
text17 = "HBAR long giriş 0.08 hedef 0.085-0.09 kaldıraç 8x"
result17 = parser.parse(text17)
if result17.entries == [0.08] and 0.085 in result17.tps and 0.09 in result17.tps:
    tests_fixed.append(17)
else:
    tests_still_broken.append((17, f"entries={result17.entries}, tps={result17.tps}"))

print(f"Fixed tests: {tests_fixed}")
print(f"Still broken: {tests_still_broken}")
print(f"\nComma decimal fix successful: {len(tests_fixed)}/3")
