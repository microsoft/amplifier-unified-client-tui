# Client boundary inventory

This repository contains the supported AHP 0.9 connected client only. Ratatui owns
rendering and unflushed editor state; Python owns local intent/projection; the
bundled official Node SDK owns protocol reducers and recovery. Native execution,
Core/Foundation composition, native history, session discovery and agent processes
belong to independently installed host/ACP packages. No native or HTTP/SSE bypass is
present. The older amplifier-app-tui repository is unchanged.

Current Python tests cover documents, observers, presentation transport/projection,
selected native renderer interactions, AHP behavior, actual connected PTYs and package
isolation. The selected renderer bodies are preserved; obsolete embedded-host tests
and engine preparation fixtures are absent. All renderer controls remain exercised
against native Ratatui. The private archive test intentionally skips when its
undistributed source archive is absent. Optional real-provider/account/device tests
are not claimed. See README for the complete supported/unavailable surface mapping.
