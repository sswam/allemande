import gradio as gr

def show_map(x):
	html_str = """
	<!DOCTYPE html>
	<html>
	<head>
		<link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"
              integrity="sha512-xodZBNTC5n17Xt2atTPuE1HxjVMSvLVW9ocqUKLsCC5CXdbqCmblAshOMASQ/keqq/sMZMZ19scR4PsZChSR7A=="
              crossorigin=""/>
		<script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"
				integrity="sha512-XQoYMqMTK8LvdxXYG3nZ448hOEQiglfqkJs1NOQV44cWnUrBc8PkAOcXy20w0vlaXaVUearIOBhiXZ5V3ynxwA=="
				crossorigin=""></script>
	</head>
	<body>
		Hello, <i>world</i>.
		<img src="https://chat.allemande.ai/src/pix/barbarella.jpg" alt="Barbarella">
	</body>
	</html>
	"""
	return html_str

gr.Interface(show_map, "text", "html").launch()
