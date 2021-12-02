.PHONY: install uninstall clean deb

package = xmrigui_1.5-2_amd64

install:
	cp xmrigui.py /usr/local/bin/xmrigui
	mkdir -p /opt/xmrigui
	cp xmrig /opt/xmrigui/
	mkdir -p /usr/share/icons/hicolor/256x256/apps
	cp xmrigui.png /usr/share/icons/hicolor/256x256/apps/
	cp xmrigui.desktop /usr/share/applications/

uninstall:
	rm /usr/local/bin/xmrigui
	rm -rf /opt/xmrigui
	rm /usr/share/icons/hicolor/256x256/apps/xmrigui.png
	rm /usr/share/applications/xmrigui.desktop

deb:
	mkdir -p $(py-package)/usr/local/bin/
	mkdir -p $(py-package)/opt/xmrigui/
	mkdir -p $(py-package)/usr/share/icons/hicolor/256x256/apps/
	mkdir -p $(py-package)/usr/share/applications/
	cp xmrigui.py $(py-package)/usr/local/bin/xmrigui
	cp xmrig $(py-package)/opt/xmrigui/
	cp xmrigui.png $(py-package)/usr/share/icons/hicolor/256x256/apps/
	cp xmrigui.desktop $(py-package)/usr/share/applications/
	dpkg-deb --build --root-owner-group $(py-package)
	rm $(py-package)/usr/local/bin/*
	rm $(py-package)/opt/xmrigui/*
	rm $(py-package)/usr/share/icons/hicolor/256x256/apps/*
	rm $(py-package)/usr/share/applications/xmrigui.desktop