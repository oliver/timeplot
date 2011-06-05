
all: qt_output_ui.py

%_ui.py: %.ui
	pyuic4 -x -o $@ $<

