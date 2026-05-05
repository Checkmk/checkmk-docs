#!/usr/bin/env ruby
# encoding: utf-8

require 'json'
require 'optparse'

def retrieve_commits() 
    commitlist = []
    IO.popen("git log --oneline --since #{@cfg["start_date"]}") { |l|
        while l.gets
            ltoks = $_.split(' ', 2)
            cid = ltoks[0]
            cmsg = ltoks[1]
            cdt = ` git show -s --format='%aI %ae' #{cid} `.strip
            commitlist.push( [ cdt, cid, cmsg ] )
        end
    }
    commitlist.each { |c|
        IO.popen("git show --pretty="" --name-only #{c[1]}") { |l|
            files = []
            while l.gets
                files.push $_.strip
            end
            c.push files
        }
    }
    return commitlist
end

def check_present(commitlist, commitdate)
    commitlist.each { |c|
        return true if c[0] == commitdate
    }
    return false
end

def switch_branch(target)
    ret = system("git checkout #{target}")
	raise "CheckoutFailed" unless ret
    system("git pull")
end

def check_against_ignores(commitinfo)
	@cfg["ignore_tickets"].each { |t|
		return false if commitinfo[2].include? t
	}
	commitinfo[3].each { |f|
		fname = f.split("/")[-1]
		unless @cfg["ignore_files"].include? fname
			return true
		end
	}
	return false
end

def check_against_forced(commitinfo)
	commitwords = commitinfo[2].gsub(',', ' ').split
	commitwords.each { |c|
		return true if @cfg["force_tickets"].include? c
	}
	commitinfo[3].each { |f|
		fname = f.split("/")[-1]
		return true if @cfg["force_files"].include? fname
	}
	return false
end

def get_config()
	@cfg = {}
	opts = OptionParser.new
	opts.on('--config', :REQUIRED) { |i|
		cfgfile = i
		@cfg = JSON.parse(File.read(cfgfile))
		@cfg['cfgfile'] = cfgfile
	}
	opts.on('--since', :REQUIRED) { |i| @cfg["start_date"] = i }
	opts.on('--only-files', :REQUIRED) { |i| @cfg["only_files"] = i.split(',') }
	opts.on('--force-tickets', :REQUIRED) { |i| @cfg["force_tickets"] = i.split(',') }
	opts.parse!
	[ "ignore_files", "ignore_tickets", "only_files", "force_files", "force_tickets" ].each { |n|
		@cfg[n] = [] unless @cfg.has_key? n
	}
end

def try_to_pick(commitinfo)
	ret = system("git cherry-pick #{commitinfo[1]}")
	unless ret
		puts "+++> Pick failed. Abort the commit and continue loop or exit? [E/a] "
		secdec = gets
		if secdec.strip == "" || secdec.strip =~ /^e/
			exit 1
		else
			commitinfo[3].each { |f| @files_with_skipped_commits.push f }
			unless system("git cherry-pick --abort")
				exit 1
			end
		end
	end
end

def ask_and_pick(missingcommits)
	missingcommits.reverse.each { |c|
		@allfiles.push c[3]
		puts "#{c[0]} + #{c[1]} + #{c[2]}"
		commitwords = c[2].gsub(',', ' ').split
		nskipped = 0
		c[3].each { |f|
			s = ""
			if @files_with_skipped_commits.include? f
				s = " <= has skipped commits!"
				nskipped += 1
			end
			puts "    #{f}#{s}"
		}
		ask = true
		decision = ""
		# Forced tickets/files first:
		if check_against_forced(c)
			defdec = "y"
			puts "===> Try to pick? [Y/n] "
		elsif !check_against_ignores(c)
			puts "===> No decision needed, ticket or files on ignore list."
			c[3].each { |f| @files_with_skipped_commits.push f }
			ask = false
		elsif nskipped > 0
			defdec = "n"
			puts "===> Try to pick? [N/y] "
		elsif commitwords.include? @cfg["keyword"]
			defdec = "y"
			puts "===> Try to pick? [Y/n] "
		else
			defdec = "n"
			puts "===> Try to pick? [N/y] "
		end
		decision = gets if ask == true
		decision = defdec if decision.strip == ""
		if decision.strip =~ /^y/i
			try_to_pick(c)
		else
			c[3].each { |f| @files_with_skipped_commits.push f }
		end
	}
end


@cfg = {}
get_config

missingcommits = []
@allfiles = []
# Hold all files with already skipped commits, these should not pick as default
@files_with_skipped_commits = []

switch_branch @cfg["pick_from_branch"]
clist = retrieve_commits
switch_branch @cfg["pick_to_branch"]
olist = retrieve_commits

clist.each { |c|
    missingcommits.push c unless check_present(olist, c[0])
}

ask_and_pick(missingcommits)


#~ @allfiles = @allfiles.sort.uniq

#~ puts "All files currently not in sync:"
#~ @allfiles.each { |f|
	#~ puts f
#~ }
