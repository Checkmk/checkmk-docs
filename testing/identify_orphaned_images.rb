#!/usr/bin/env ruby

# Identify orphaned images
#
# Takes two CLI parameters:
# 
# * the directory containing the subdirectories latest/ and saas/ with the rendered user guide
# * the source directory containing the images/ folder
#
# The script parses all HTML files in the subdirectories en/ and de/ of the latest/ and saas/ user
# guide and compares the src attributes of all image nodes found against the list of PNG, JPG and
# SVG files generated from the images folder.
#
# In the end a list of images that are not used anywhere is generated. If a third parameter is
# is specified, this is treated as a file name where to write that list.
#
# Use this script after each release after branching to remove now obsolete images.

require 'nokogiri'

htmlfolder = ARGV[0]
imgfolder = ARGV[1]
imglist = []        # images in folder
imgsrclist = []     # images in source tags

Dir.entries(imgfolder).each { |f|
    if f =~ /\.(jpg|jpeg|png|svg)$/i
        imglist.push f unless (f =~ /original/ || f =~ /internal_reference/)
    end
}

[ "de", "en" ].each { |lang|
    [ "latest", "saas" ].each { |branch|
        dir = "#{htmlfolder}/#{branch}/#{lang}"
        Dir.entries(dir).each { |f|
            fn = "#{dir}/#{f}"
            if File.file?(fn)
                xdoc = Nokogiri::HTML.parse(File.open(fn).read)
                images = xdoc.search("img")
                images.each { |i|
                    p = i["src"].split("/")[-1]
                    imgsrclist.push p
                    # puts p
                }
            end
        }
    }
}

# Compact!
imglist = imglist.sort.uniq
imgsrclist = imgsrclist.sort.uniq
notneeded = imglist - imgsrclist

puts "Images available: #{imglist.size}"
puts "Images referenced: #{imgsrclist.size}"
puts "Images not in intersection: #{notneeded.size}"

unless ARGV[2].nil?
    puts
    fout = File.new(ARGV[2], "w")
    notneeded.each { |n|
        fout.write n
        fout.write "\n"
    }
    fout.close
else
    notneeded.each { |n| puts n }
end
