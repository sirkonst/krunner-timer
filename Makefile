all: pack

pack:
	cd src/ && zip -r ../krunner-alarmtimer.zip .

install: pack
	plasmapkg --type runner -r timer || true
	plasmapkg --type runner -r alarmtimer || true
	plasmapkg --type runner -i krunner-alarmtimer.zip

dev:
	rm ~/.kde4/share/config/krunner-alarmtimer.notifyrc | true
	rm ~/.kde4/share/apps/krunner-timer/krunner-alarmtimer.notifyrc | true
	plasmapkg --type runner -u src/
	kquitapp krunner
	sleep 1
	krunner
