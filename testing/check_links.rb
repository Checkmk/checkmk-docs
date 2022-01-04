#!/usr/bin/env ruby
# encoding: utf-8

require 'net/http'
require 'fileutils'
require 'optparse' 

# Create a class for each file in both translations:

class DocItem 
	
	# Start with a filename
	def initialize(langs, file, target_dir, excludes=[], includes=[])
		@langs = langs
		@file = file
		@locdocs = Hash.new
		langs.each { |l|
			if File.exists?(l + "/" + file)
				@locdocs[l] = DocItemLocalized.new(l, file, target_dir, excludes, includes)
			end
		}
	end
	attr_reader :locdocs, :file
	
	def check_missing_langs
		@langs.each { |l|
			puts "Missing translation (" + l + ") for file: " + @file unless @locdocs.has_key?(l)
		}
	end
	
	def compare_related 
		# Only works for two languages!
		if @locdocs.has_key?(@langs[0]) && @locdocs.has_key?(@langs[1])
			delta = @locdocs[@langs[0]].related - @locdocs[@langs[1]].related
			if delta.size > 0
				puts "Differences in related, file: " + @file + ", links: " + delta.join(", ")
			end
		end
	end
	
	def check_internal(alldocs) 
		@langs.each { |l|
			@locdocs[l].check_internal(alldocs) if @locdocs.has_key? l
		}
	end
	
	def check_external(alldocs)
		# Check external links originating from this document 
		@langs.each { |l|
			@locdocs[l].check_external(alldocs) if @locdocs.has_key? l
		}
	end
	
	def check_full_links
		@langs.each { |l|
			@locdocs[l].check_full_links if @locdocs.has_key? l
		}
	end
	
	def write_back 
		@langs.each { |l|
			@locdocs[l].write_back if @locdocs.has_key? l
		}
	end
end

class DocItemLocalized
	

	def initialize(lang, file, target_dir, excludes=[], includes=[])
		@lang = lang
		@file = file
		@excludes = excludes
		@includes = includes
		@lines = Array.new   # array of unedited lines
		@anchors = Array.new # anchors provided by this document
		@impanchors = Array.new # implicite anchors created from headings
		@related = Array.new # array of related links
		@changes = Hash.new # Contains only changed lines
		@changed = false
		@target_dir = target_dir
		inside_related = false
		linenum = 0 
		File.open(lang + "/" + file).each {|line|
			# tokenize the line:
			ltoks = line.strip.split
			# Find anchors
			if line.strip =~ /^\[\#(.*?)\]/
				@anchors.push $1
			elsif line.strip =~ /^=/
				imp= line.gsub(/(\W|\d)/, "")
				@impanchors.push imp
				# puts imp.downcase
			end
			inside_related = true if line.strip == "{related-start}"
			inside_related = false if line.strip == "{related-end}"
			# Store related links
			if inside_related && line =~ /link:(.*?)\.html/
				@related.push $1
			end
			if inside_related && line =~ /xref:(.*?)\#/
				@related.push $1
			end
			# Store the line
			@lines.push line
			linenum += 1
		}
		@related.sort!
	end
	attr_reader :lang, :file, :related, :anchors, :lines, :impanchors
	
	def check_internal(alldocs)
		linenum = 0
		@lines.each { |line|
			linenum += 1
			# tokenize the line:
			ltoks = line.strip.split
			ltoks.each { |t|
				if t =~ /xref\:(.*?)\#(.*?)\[/ || t =~ /xref\:(.*?)\.html/
					# external reference
				elsif t =~ /xref\:([a-zA-Z0-9_-]*?)\[/
					# internal reference
					# puts t + " " + $1
					ref = $1
					puts "Broken page internal link: #{@file} (#{@lang}, " + 
						"line #{linenum}): #{ref}" unless @anchors.include? ref
					alldocs.each { |d|
						unless d.locdocs[@lang].nil?
							if d.locdocs[@lang].file == ref + ".asciidoc"
								modline = line.gsub(/xref\:([a-zA-Z0-9_-]*?)\[/, 'xref:\1#[')
								puts "Modifying file: #{@file} (#{lang}), line: #{linenum}"
								puts "- " + line
								puts "+ " + modline
								@changes[linenum - 1] = modline
							end
						end
					}
				end
			}
			
		}
	end
	
	def check_external(alldocs)
		linenum = 0
		inside_related = false
		@lines.each { |line|
			linenum += 1
			# Check whether we are in related section:
			inside_related = true if line.strip == "{related-start}"
			inside_related = false if line.strip == "{related-end}"
			# tokenize the line:
			ltoks = line.strip.split
			ltoks.each { |t|
				target = ""
				deep = ""
				if t =~ /xref\:(.*?)\.html\#(.*?)\[/
					# external reference
					target = $1
					deep = $2
				elsif t =~ /xref\:(.*?)\#(.*?)\[/
					# external reference
					target = $1
					deep = $2
				elsif t =~ /xref\:(.*?)\.html/
					# external reference, assume no anchors are set
					target = $1
				elsif t =~ /link\:(https+\:\/\/)(.*?)\[/
					# ignore
				elsif t =~ /link\:ftp\:\/\/(.*?)\[/
					# ignore 
				elsif t =~ /link\:(.*?)\.html\#(.*?)\[/
					# external reference
					target = $1
					deep = $2
				elsif t =~ /link\:(.*?)\.html\[/	
					# external reference
					target = $1
				end
				if target.length > 0
					tgt_found = false
					tgt_found = true if target == "check_plugins_catalog" # forward
					anchor_found = false
					alldocs.each { |d|
						unless d.locdocs[@lang].nil?
							if d.locdocs[@lang].file == target + ".asciidoc"
								tgt_found = true 
								if deep.length > 0
									#puts target + " " + deep 
									d.locdocs[@lang].anchors.each { |a|
										#puts "       #{a}"
										anchor_found = true if a == deep
										#puts "              FOUND!" if a == deep
									}
									if anchor_found == false
										d.locdocs[@lang].impanchors.each { |a|
											if a == deep.gsub(/(\W|\d)/, "")
												anchor_found = true
												puts "Implicit target anchor, file: #{@file} (#{lang}), line: #{linenum}, target: #{target}##{deep}"
											end
										}
										
									end
								end
							end
						end
					}
					if tgt_found == false
						puts "Missing link target, file: #{@file} (#{lang}), line: #{linenum}, target: #{target}"
					elsif deep.length > 0 && anchor_found == false 
						puts "Missing target anchor, file: #{@file} (#{lang}), line: #{linenum}, target: #{target}##{deep}"
					else
						modline = line
						if t =~ /link\:(.*?)\.html\#(.*?)\[/
							modline = modline.gsub(/link\:(.*?)\.html\#(.*?)\[/, 'xref:\1#\2[')
						end
						if t =~ /link\:(.*?)\.html\[/	
							modline = modline.gsub(/link\:(.*?)\.html\[/, 'xref:\1[')
						end
						unless ( line == modline || inside_related == true )
							puts "Modifying file: #{@file} (#{lang}), line: #{linenum}"
							puts "- " + line
							puts "+ " + modline
							@changes[linenum - 1] = modline
						end
					end
				end
			}
			
		}
		puts "Changed #{@changes.size} lines of file #{@file} (#{lang})" if @changes.size > 0
	end
	
	def check_full_links
		linenum = 0
		@lines.each { |line|
			linenum += 1
			# tokenize the line:
			ltoks = line.strip.split
			ltoks.each { |t|
				http_detected = false
				fullurl = ""
				requrl = ""
				linktext = ""
				if t =~ /link\:(https+\:\/\/)(.*?)\#(.*?)\[(.*?)\]/
					# puts $1 + " " + $2 + " " + $3
					fullurl = $1 + $2 + "#" + $3
					requrl = $1 + $2
					linktext = $4
					http_detected = true if $1 == "http://"
				elsif t =~ /link\:(https+\:\/\/)(.*?)\[(.*?)\]/
					fullurl = $1 + $2
					linktext = $3
					requrl = fullurl
					http_detected = true if $1 == "http://"
				elsif t =~ /link\:ftp\:\/\/(.*?)\[/
					puts "FTP link detected, please deprecate: #{@file} (#{@lang}, " + 
						"line #{linenum}): #{$1}"
				elsif t =~ /link\:(.*?)\[/
					puts "Internal link uses link instead of xref, fix needed: #{@file} (#{@lang}, " + 
						"line #{linenum}): #{$1}"
				end
				puts "Unsafe external link: #{@file} (#{@lang}, " + 
						"line #{linenum}): #{fullurl}" if http_detected == true
				puts "Missing circonflex: #{@file} (#{@lang}, " + 
						"line #{linenum}): #{requrl}" if linktext.length > 0 && !(linktext =~ /\^$/)
				# Do not use for now, there are many duplicate links
				#if requrl.length > 0 
				#	# puts "Checking: " + fullurl
				#	begin
				#		uri = URI(requrl)
				#		Net::HTTP.get(uri) # => String
				#	rescue
				#		puts "Broken URL: #{@file} (#{@lang}, " + 
				#			"line #{linenum}): #{fullurl}"
				#	end
				#end
			}
			
		}
	end
	
	def write_back
		return if @changes.size < 1
		return if @excludes.include?(@lang + "/" + @file)
		if @includes.size > 0 
			return unless @includes.include?(@lang + "/" + @file)
		end
		FileUtils.mkdir_p @target_dir + "/" + @lang
		outhandle = File.new(@target_dir + "/" + @lang + "/" + @file, "w")
		lct = 0
		@changes.each { |k,v|
			@lines[k] = v
		}
		@lines.each { |l|
			outhandle.write l
		}
		outhandle.close 
	end
	
end

# Do not write back these files except stated otherwise:
@exclude_files = [
	"de/appliance_usage.asciidoc",
	"en/appliance_usage.asciidoc",
	"de/cma_rack1_quick_start.asciidoc",
	"en/cma_rack1_quick_start.asciidoc",
	"de/cma_virt1_quick_start.asciidoc",
	"en/cma_virt1_quick_start.asciidoc",
	"de/menu.asciidoc",
	"en/menu.asciidoc",
	"de/index.asciidoc",
	"en/index.asciidoc" ]
@include_files = []
@write_back = false
@target_dir = "/tmp/checkmk_docs"

# Now parse CLI options:
opts = OptionParser.new 
opts.on('-x', '--exclude-files', :REQUIRED )    { |i| @exclude_files = i.split(",") }
opts.on('-w', '--write-back', :REQUIRED )    { |i| 
	@target_dir = i
	@write_back = true
}
opts.on('-o', '--only-files', :REQUIRED )    { |i| 
	@include_files = i.split(",")
}
opts.parse!

@all_doc_items = Array.new # contains one docItem per element

# Read files into an array

@allfiles = []
@langs = [ "de", "en" ]
@langs.each { |l|
	Dir.entries(l).each { |f|
		@allfiles.push f if f =~ /\.asciidoc$/
	}
	@allfiles.uniq!
}

# Now create the doc items

@allfiles.each { |f|
	@all_doc_items.push(DocItem.new(@langs, f, @target_dir, @exclude_files, @include_files))
}

@all_doc_items.each { |d|
	d.check_missing_langs
}
@all_doc_items.each { |d|
	d.compare_related
}
@all_doc_items.each { |d|
	d.check_internal(@all_doc_items)
}
@all_doc_items.each { |d|
	d.check_external(@all_doc_items)
}
@all_doc_items.each { |d|
	d.check_full_links
}
if @write_back == true
	@all_doc_items.each { |d|
		d.write_back
	}
end









