chat:
	nt chat run
	uvicorn chat-api:app --reload  # --reload-include *.csv

stream:
	nt stream run
	cd rooms ; uvicorn stream:app --app-dir .. --reload  --reload-dir .. --port 8001

nginx:
	nt nginx run
	inotifywait -q -m -e modify nginx | while read e; do v sudo systemctl restart nginx; done

logs:
	nt logs
	tail -f /var/log/nginx/access.log /var/log/nginx/error.log

perms:
	adm/perms

.PHONY: run nginx perms
