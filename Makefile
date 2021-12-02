.PHONY: install uninstall clean deb

package = xmrigui_1.6-1_amd64

install:
	cp xmrigui.py /usr/local/bin/xmrigui
	mkdir -p /opt/xmrigui
	cp xmrig /opt/xmrigui/
	mkdir -p /usr/share/icons/hicolor/256x256/apps
	cp xmrigui.png /usr/share/icons/hicolor/256x256/apps/
	cp xmrigui.desktop /usr/share/applications/
	cp org.freedesktop.policykit.xmrigui.policy /usr/share/polkit-1/actions/org.freedesktop.policykit.xmrigui.policy

uninstall:
	rm /usr/local/bin/xmrigui
	rm -rf /opt/xmrigui
	rm /usr/share/icons/hicolor/256x256/apps/xmrigui.png
	rm /usr/share/applications/xmrigui.desktop
	rm /usr/share/polkit-1/actions/org.freedesktop.policykit.xmrigui.policy

deb:
	mkdir -p $(package)/usr/local/bin/
	mkdir -p $(package)/opt/xmrigui/
	mkdir -p $(package)/usr/share/icons/hicolor/256x256/apps/
	mkdir -p $(package)/usr/share/applications/
	mkdir -p $(package)/usr/share/polkit-1/actions/
	cp xmrigui.py $(package)/usr/local/bin/xmrigui
	cp xmrig $(package)/opt/xmrigui/
	cp xmrigui.png $(package)/usr/share/icons/hicolor/256x256/apps/
	cp xmrigui.desktop $(package)/usr/share/applications/
	cp org.freedesktop.policykit.xmrigui.policy $(package)/usr/share/polkit-1/actions/org.freedesktop.policykit.xmrigui.policy
	dpkg-deb --build --root-owner-group $(package)
	rm $(package)/usr/local/bin/*
	rm $(package)/opt/xmrigui/*
	rm $(package)/usr/share/icons/hicolor/256x256/apps/*
	rm $(package)/usr/share/applications/xmrigui.desktop