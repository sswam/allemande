#!/bin/bash
(time v webchat-user-fix ; time v webchat-user-audit ; time v webchat-user-conflicts ; time v webchat-user-nag < ~/users.rec) 2>&1 | tee ~/users.log
