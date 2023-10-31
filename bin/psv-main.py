#!/usr/bin/env python3.10
import sys
import psv.main

sys.exit(psv.main.Main().run(sys.argv).exit_code)
