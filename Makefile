all: pack

pack:
	cd src/ && zip -r ../krunner-timer.zip .

install: pack
	plasmapkg --type runner -r timer || true
	plasmapkg --type runner -i krunner-timer.zip

dev:
	rm ~/.kde4/share/config/krunner-timer.notifyrc | true
	rm ~/.kde4/share/apps/krunner-timer/krunner-timer.notifyrc | true
	plasmapkg --type runner -u src/
	kquitapp krunner
	sleep 1
	krunner
