require 'nokogiri'
require 'sort_kana_jisx4061'

# Function to extract kana reading (furigana) or fallback to plain text
def extract_kana(entry)
  rt = entry.at_css('h4 ruby rt')
  if rt
    rt.text.strip
  else
    h4 = entry.at_css('h4')
    h4 ? h4.text.strip : ''
  end
end

# Input/output files from command line arguments or default values
input_file  = ARGV[0] || 'glossary_unsorted_ja.html'
output_file = ARGV[1] || 'glossary_sorted_ja.html'

# Read source HTML file
doc = Nokogiri::HTML(File.read(input_file), nil, 'UTF-8')

# --- Part 1: Sort div.sect3 entries in the main section ---

# Find the specific h3 to locate the parent div.sect2
h3 = doc.at_css('h3#heading__checkmk_specific_terms')
parent_div = h3 ? h3.ancestors('div.sect2').first : nil

if parent_div.nil?
  puts "Parent div sect2 for section 1 not found."
  exit 1
end

# Extract div.sect3 entries to sort
entries = parent_div.xpath('.//div[contains(@class,"sect3")]')

puts "Number of div.sect3 entries found: #{entries.size}"

# Sort according to JIS X 4061 order based on extracted kana
sorted_entries = sort_kana_jisx4061_by(entries) do |entry|
  extract_kana(entry).to_s  # force to string
end

# Remove old entries
entries.each(&:remove)

# Re-insert sorted entries
sorted_entries.each do |entry|
  parent_div.add_child(entry)
end

puts "Main entries sorted using JIS X 4061."

# --- Part 2: Sort the table of contents (TOC) ---

toc_div = doc.at_css('div#toc.toc2')

if toc_div.nil?
  puts "TOC not found, proceeding to save without sorting TOC."
else
  root_ul = toc_div.at_css('ul.sectlevel2')
  if root_ul.nil?
    puts "Root TOC list not found, proceeding to save without sorting TOC."
  else
    nested_ul = root_ul.at_css('li > ul.sectlevel2')
    if nested_ul.nil?
      puts "TOC entries list not found, proceeding to save without sorting TOC."
    else
      entries_toc = nested_ul.css('li')

      # Sort the TOC using the same extract_kana logic
      sorted_toc = sort_kana_jisx4061_by(entries_toc) do |li|
        text = li.at_css('a')&.text&.strip || ''
        text.to_s
      end

      entries_toc.each(&:remove)
      sorted_toc.each { |li| nested_ul.add_child(li) }

      puts "TOC sorted using JIS X 4061."
    end
  end
end

# Final save of the sorted HTML file
File.write(output_file, doc.to_html)

puts "Sorted Japanese glossary saved to #{output_file}"
