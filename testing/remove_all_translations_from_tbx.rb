#!/usr/bin/env ruby
# encoding: utf-8

require "nokogiri"

indata = File.read(ARGV[0])
inxml = Nokogiri::XML.parse(indata)

rcount = 0

inxml.search(".//body/termEntry/langSet[@xml:lang='en_US']/tig/term").each { |n| 
    if n.inner_text.size > 0
        puts "Removing: " + n.content
        n.content = ""
        rcount += 1
    end
}

puts "Removed #{rcount} strings."

File.open(ARGV[1], "w") { |f| f.write(inxml) }