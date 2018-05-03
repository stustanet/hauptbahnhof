socat -d PTY,link=/tmp/rupprechtemulator,echo=0 "EXEC:python3 rupprechtemulator.py ...,pty,raw",echo=0
