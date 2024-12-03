static_files = $(wildcard static/*.html) $(wildcard static/*.css) $(wildcard static/*.js) $(wildcard static/*.json) $(wildcard static/*.png)

build.stamp: $(static_files)
	./update_service_worker_version.sh
	touch build.stamp
