require 'nokogiri'
require 'set'
require 'unicode_utils'

# Sorts the glossary entries alphabetically, driven by the table of contents.
# Each TOC link points to an entry heading. The script finds the lowest common
# ancestor of all entry headings and sorts its children (one block per entry).

NOTICE_RE = /machine translation/i

def normalize_text(text)
  UnicodeUtils.nfkd(text.to_s.strip.downcase).gsub(/\p{Mn}/, '')
end

def heading?(node)
  node.element? && node.name =~ /\Ah[1-6]\z/
end

def capitalize_first(node)
  return unless node
  t = node.xpath('.//text()').find { |x| !x.content.strip.empty? }
  return unless t
  t.content = t.content.sub(/\A(\s*)(\p{Ll})/) { "#{$1}#{$2.upcase}" }
end

input_file  = ARGV[0] || 'glossary_unsorted.html'
output_file = ARGV[1] || 'glossary_sorted.html'
doc = Nokogiri::HTML(File.read(input_file), nil, 'UTF-8')

# --- TOC list of glossary entries (the list with the most items) ---
toc_div = doc.at_css('#toc')
abort 'TOC (#toc) not found, nothing changed.' unless toc_div
toc_ul = toc_div.css('ul').max_by { |ul| ul.xpath('./li').size }
abort 'No TOC list found, nothing changed.' unless toc_ul
items = toc_ul.xpath('./li')
puts "TOC list: #{items.size} entries"

# --- Locate each entry heading in the body ---
ids = items.map { |li| li.at_css('a')&.[]('href').to_s.sub(/\A#/, '') }
targets = ids.map { |id| id.empty? || id.include?("'") ? nil : doc.at_xpath("//*[@id='#{id}']") }
missing = ids.each_with_index.select { |_, i| targets[i].nil? }.map(&:first)
abort "Entries not found in body (nothing changed): #{missing.first(10).join(', ')}" if missing.any?

title_nodes = targets.map do |t|
  heading?(t) ? t : (t.at_xpath('.//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]') || t)
end
t0 = targets.first
puts "Entry target example: <#{t0.name} id=\"#{t0['id']}\" class=\"#{t0['class']}\"> text: #{t0.text.strip[0, 50].inspect}"

# --- Lowest common ancestor of all entries ---
anc_sets = targets.map { |t| t.ancestors.map(&:pointer_id).to_set }
lca = targets.first.ancestors.to_a.find { |a| anc_sets.all? { |s| s.include?(a.pointer_id) } }
abort 'No common container found, nothing changed.' unless lca
puts "Common container: <#{lca.name} class=\"#{lca['class']}\">"

# --- Start node of each entry = its ancestor (or itself) directly under the LCA ---
starts = targets.map do |t|
  ([t] + t.ancestors.to_a).find { |n| n.parent && n.parent.pointer_id == lca.pointer_id }
end
if starts.map(&:pointer_id).uniq.size != starts.size
  abort 'Several entries share the same block, nothing changed.'
end
start_keys = starts.map(&:pointer_id).to_set

# --- Block of nodes for each entry ---
blocks = starts.map do |s|
  next [s] unless heading?(s)
  level = s.name[1].to_i
  nodes = [s]
  sib = s.next_sibling
  while sib
    break if start_keys.include?(sib.pointer_id)
    break if heading?(sib) && sib.name[1].to_i <= level
    nodes << sib
    sib = sib.next_sibling
  end
  nodes
end

# --- Pull the machine translation notice out of the entries ---
notices = []
blocks.flatten.each do |n|
  next unless n.element?
  if n.text =~ NOTICE_RE && n.text.length < 800 && !title_nodes.any? { |h| h && h.ancestors.include?(n) }
    notices << n
    next
  end
  cands = n.xpath('.//div').select { |d| d.text =~ NOTICE_RE && d.text.length < 800 }
  outer = cands.reject { |d| cands.any? { |o| o != d && d.ancestors.include?(o) } }
  notices.concat(outer)
end
blocks.each { |b| b.reject! { |n| notices.include?(n) } }

# --- Reorder the body (sort key = TOC link text of each entry) ---
title_nodes.each { |h| capitalize_first(h) }
items.each { |li| capitalize_first(li.at_css('a')) }
keys = items.map { |li| li.at_css('a')&.text.to_s.strip }
empty = keys.count(&:empty?)
abort "#{empty} TOC entries have no text, nothing changed." if empty > 0
order = blocks.each_index.sort_by { |i| [normalize_text(keys[i]), i] }

marker = Nokogiri::XML::Node.new('span', doc)
blocks.first.first.add_previous_sibling(marker)
blocks.flatten.each(&:unlink)
notices.each(&:unlink)
order.each { |i| blocks[i].each { |n| marker.add_previous_sibling(n) } }
first_node = blocks[order.first].first
notices.each { |n| first_node.add_previous_sibling(n) }
marker.unlink

puts "Body entries sorted: #{blocks.size} (notice moved to top: #{notices.size})"
puts "First entries: #{order.first(5).map { |i| keys[i] }.join(' | ')}"

# --- Sort the TOC (same order as the body) ---
sorted_items = order.map { |i| items[i] }
items.each(&:unlink)
sorted_items.each { |li| toc_ul.add_child(li) }
puts "TOC sorted: #{items.size} entries"

File.write(output_file, doc.to_html)
puts "Sorted glossary saved to #{output_file}"
