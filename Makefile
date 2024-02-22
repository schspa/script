# -*- coding:utf-8 -*-
ifeq ($(PREFIX),)
	PREFIX := /usr/local
endif

install:
	install -m 755 bot_notify.py $(DESTDIR)$(PREFIX)/bin/
	install -m 755 cf_ddns.py $(DESTDIR)$(PREFIX)/bin/
	install -m 644 etc/systemd/cf-ddns.timer /usr/lib/systemd/system
	install -m 644 etc/systemd/cf-ddns.service /usr/lib/systemd/system
