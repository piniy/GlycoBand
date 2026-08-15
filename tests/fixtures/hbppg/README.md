# Hb-PPG Test Fixtures

Tests generate small participant CSVs at runtime. Every fixture must retain an explicit participant
ID, the ordered real channel names `660nm/730nm/850nm/940nm`, a declared duration, and a glucose
reference or explicit missing token. Identical copied wavelength content is an invalid fixture unless
the test is specifically proving that the audit rejects it.

Fixtures are software tests only and are not biological evidence.

