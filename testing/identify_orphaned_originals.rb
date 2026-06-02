#!/usr/bin/env ruby

# Identify orphaned original images
#
# Takes two CLI parameters:
#
# * the directory to scan fo images
# * the file to write a list to (optional, if omitted STDOUT is used)

imgfolder = ARGV[0]
imglist = []	# store the images without suffix
origlist = [] 	# store the images with the orig suffix

Dir.entries(imgfolder).each { |f|
    if f =~ /\.(jpg|jpeg|png|svg|xcf)$/i
		if f =~ /_original\./
			origlist.push f.gsub(/_original\.[a-z]*?$/, '')
		else
			imglist.push f.gsub(/\.[a-z]*?$/, '')
		end
    end
}

nooriginal = origlist - imglist

if ARGV[1].nil?
	nooriginal.each { |n| puts n }
else
	fout = File.new(ARGV[1], "w")
    nooriginal.each { |n|
        fout.write n
        fout.write "\n"
    }
    fout.close
end
