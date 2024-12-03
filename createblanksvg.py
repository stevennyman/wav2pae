import verovio

tk = verovio.toolkit()

tk.setOptions({"inputFrom": "pae"})

tk.loadData('''{
    "clef": "G-2",
    "keysig": "",
    "timesig": "4/4",
    "data": ""
}'''
)                           

o = tk.renderToSVGFile("out_Original.svg")
o = tk.renderToSVGFile("out_Result.svg")