require 'nokogiri'
require 'unicode_utils'

# Function to normalize text by removing accents for proper sorting
def normalize_text(text)
  UnicodeUtils.nfkd(text).gsub(/\p{Mn}/, '')
end

# Input/output filenames from command-line arguments or default
input_file  = ARGV[0] || 'glossary_unsorted.html'
output_file = ARGV[1] || 'glossary_sorted.html'

# Read the source HTML file
doc = Nokogiri::HTML(File.read(input_file), nil, 'UTF-8')

# --- Part 1: Sort the div.sect3 entries in the main section ---

# Find the specific h3 to locate the parent div (sect2)
h3 = doc.at_css('h3#heading__checkmk_specific_terms')
parent_div = h3 ? h3.ancestors('div.sect2').first : nil

if parent_div.nil?
  puts "Parent div sect2 for section 1 not found."
  exit 1
end

# Extract the div.sect3 entries (the entries to sort)
entries = parent_div.xpath('.//div[contains(@class,"sect3")]')

puts "Number of div.sect3 entries found: #{entries.size}"

# Sort the entries by the text of the h4 inside each div.sect3, normalized
sorted_entries = entries.sort_by do |entry|
  h4 = entry.at_css('h4')
  text = h4 ? h4.text.strip.downcase : ''
  normalize_text(text)
end

# Remove the original entries from the parent
entries.each(&:remove)

# Re-insert in sorted order
sorted_entries.each do |entry|
  parent_div.add_child(entry)
end

puts "Main entries sorted."

# --- Part 2: Sort the table of contents (TOC) ---

# Find the TOC div
toc_div = doc.at_css('div#toc.toc2')

if toc_div.nil?
  puts "TOC not found, proceeding to save without sorting TOC."
else
  # Find the root ul.sectlevel2 list
  root_ul = toc_div.at_css('ul.sectlevel2')
  if root_ul.nil?
    puts "Root TOC list not found, proceeding to save without sorting TOC."
  else
    # Find the nested list containing TOC entries
    nested_ul = root_ul.at_css('li > ul.sectlevel2')
    if nested_ul.nil?
      puts "TOC entries list not found, proceeding to save without sorting TOC."
    else
      # Extract the <li> elements of the TOC entries
      entries_toc = nested_ul.css('li')

      # Sort by the text of the <a> link inside each li, normalized
      sorted_toc = entries_toc.sort_by do |li|
        text = li.at_css('a').text.strip.downcase
        normalize_text(text)
      end

      # Remove the original li elements
      entries_toc.each(&:remove)

      # Re-insert the sorted li elements
      sorted_toc.each { |li| nested_ul.add_child(li) }

      puts "TOC sorted."
    end
  end
end

# Final save of the sorted file
File.write(output_file, doc.to_html)

puts "Sorted glossary saved to #{output_file}"
