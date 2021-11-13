.PHONY: build install uninstall clean deb

package = xmrigui_1.4-1_amd64
py-package = xmrigui_1.4-1-python_amd64

build:
	pyinstaller --onefile -w xmrigui.py

install:
	cp dist/xmrigui /usr/local/bin/
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

clean:
	rm -rf __pycache__
	rm -rf build
	rm -rf dist
	rm -rf xmrigui.spec

deb:
	mkdir -p $(package)/usr/local/bin/
	mkdir -p $(package)/opt/xmrigui/
	mkdir -p $(package)/usr/share/icons/hicolor/256x256/apps/
	mkdir -p $(package)/usr/share/applications/
	cp dist/xmrigui $(package)/usr/local/bin/
	cp xmrig $(package)/opt/xmrigui/
	cp xmrigui.png $(package)/usr/share/icons/hicolor/256x256/apps/
	cp xmrigui.desktop $(package)/usr/share/applications/
	dpkg-deb --build --root-owner-group $(package)
	rm $(package)/usr/local/bin/*
	rm $(package)/opt/xmrigui/*
	rm $(package)/usr/share/icons/hicolor/256x256/apps/*
	rm $(package)/usr/share/applications/xmrigui.desktop

py-install:
	cp xmrigui.py /usr/local/bin/xmrigui
	mkdir -p /opt/xmrigui
	cp xmrig /opt/xmrigui/
	mkdir -p /usr/share/icons/hicolor/256x256/apps
	cp xmrigui.png /usr/share/icons/hicolor/256x256/apps/
	cp xmrigui.desktop /usr/share/applications/

py-deb:
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