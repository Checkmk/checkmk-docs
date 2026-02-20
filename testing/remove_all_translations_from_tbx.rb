#!/usr/bin/env ruby
# encoding: utf-8

require "nokogiri"

indata = File.read(ARGV[0])
inxml = Nokogiri::XML.parse(indata)

outdata = '<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE martif PUBLIC "ISO 12200:1999A//DTD MARTIF core (DXFcdV04)//EN" "TBXcdv04.dtd">
<martif type="TBX" xml:lang="en">
    <martifHeader>
        <fileDesc>
            <sourceDesc>
                <p>Translate Toolkit</p>
            </sourceDesc>
        </fileDesc>
    </martifHeader>
    <text>
        <body>
            
        </body>
    </text>
</martif>'
outxml = Nokogiri::XML.parse(outdata)

rcount = 0

outxml.search(".//body/termEntry").each { |n|
    n.remove
}
body = outxml.search(".//body")[0]

inxml.search(".//body/termEntry").each { |n|
    m = n.search("./langSet[@xml:lang='en_US']/tig/term")[0]
    if m.inner_text.size > 0
        puts "Removing: " + m.content
        m.content = ""
        rcount += 1
        body.add_child(n.clone)
    end
}

puts "Removed #{rcount} strings."

File.open(ARGV[1], "w") { |f|
    f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
    f.write(outxml.to_html)
}