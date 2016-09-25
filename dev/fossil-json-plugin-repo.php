<?php
/**
 * api: php
 * type: handler
 * title: Common.json repo list
 * description: Create json dict of selected fossil repository contents
 * version: 0.1
 * depends: fossil:json
 * doc: http://fossil.include-once.org/streamtuner2/wiki?name=plugin+meta+data
 *      https://pypi.python.org/pypi/pluginconf/
 *
 * Generates a „common-repo“-json list for files from a fossil repository.
 *
 *  · Used for streamtuner2 plugin manager - to refresh module list directly
 *    from repositories.
 *
 *  · Extracts key:value comments as seen above.
 *
 *  · Accepts PATH_INFO specifiers using glob patterns `/reponame/src*dir/*.ext`.
 *
 *  · You'll probably want to hook it beside the actual fossil server, using
 *    using a RewriteRule or ScriptAliasMatch.
 *    e.g.
 *        RewriteRule   ^(/?)repo.json/(.+)$ $1plugins.php/$2
 *
 *  · Each entry carries a faux $type, $dist and $file references, and all
 *    extracted meta fields, no docs. (= The crudest implementation so far.)
 *
 */


// run
$p = opts() and gen($p);



/**
 * Request params
 * [WHITELIST]
 *
 *  · assert alphanumeric repository.fossil name
 *  · limit allowed glob specifiers and file paths
 *
 */
function opts() {
    preg_match(
        "~^
           /(?<repo>[\w-]+)            # fossil basename
           /(?<glob>
              (?:
               [/\w.-]+                # basedir prefix
               [*]?                    
              ){0,3}                   # up to 3 *-glob segments
            )
        $~x",
        $_SERVER["PATH_INFO"], $groups
    );
    return $groups;
}


/**
 * Handler
 * [MAIN]
 *
 *  · invoked with $repo="projectname" and $glob="lib/*.src"
 *  · scans files, converts into repo.json, and outputs that
 *
 */
function gen($kwargs) {
    extract($kwargs);
    header("Content-Type: json/common-repo; x-ver=0");
    exit(
        json_encode(
            common_repo(
                query_files("/fossil.d/$repo.fossil", $glob),
                $repo
            ),
            JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT
        )
    );
}



/**
 * Read glob-specified files from repository
 * [EXEC]
 *
 *  · scans fossil repos for given filespec, e.g. "lib/plugins/*.py"
 *  · returns just first 2K from content
 *
 */
function query_files($R, $glob) {
   $r = [];
   if (!file_exists($R)) {
       return $r;
   }

   // loop through files
   $glob = escapeshellarg(preg_replace("~[^/\w.*-]~", "", $glob));
   $sql = escapeshellarg("
      SELECT  name AS name,  uuid,   SUBSTR(HEX(CONTENT(uuid)),1,2048) AS content
         FROM (SELECT  filename.name, bf.uuid, filename.fnid 
               FROM filename  JOIN mlink ON mlink.fnid=filename.fnid JOIN blob bf ON bf.rid=mlink.fid
                    JOIN event ON event.objid=mlink.mid
               WHERE (mlink.fnid NOT IN (SELECT fnid FROM mlink WHERE fid=0))
                     AND filename.name GLOB $glob
               GROUP BY filename.name
               ORDER BY event.mtime DESC
              )
   ");

   // Just retrieve as CSV list from fossil directly,
   // instead of using PDO handle and `fossil artifact` on each UUID
   $pipe = popen("fossil sqlite -R $R \".mode csv\" $sql", "rb");
   while ($row = fgetcsv($pipe, 0, ",", '"', '"')) {

      // skip emtpy rows
      if (count($row) != 3) {
          continue;
      }
      // add file
      $r[$row[0]] = hex2bin($row[2]);
   }

   return $r;
}


/**
 * Convert attributes into list
 * [TRANSFORM]
 *
 *  · from $fn=>$meta dict to [$pkg, $pkg] list
 *
 */
function common_repo($files, $R) {

    // extend each PMD key:value list
    $repo = meta_extract($files);
    foreach ($repo as $fn => $meta) {
    
        // basename, extension
        $id = strtok(basename($fn), ".");
        $ext = pathinfo($fn, PATHINFO_EXTENSION);
        $dir = basename(dirname($fn));
        
        // add some stub fields
        $meta += [
            "type" => "unknown",
            "api" => "$R",
            "title" => null,
            "description" => null,
            "version" => null,
        ];
        
        // common repo fields carry a `$` sigil
        $repo[$fn] = array_merge(
            [
                "\$name" => $id,                         # package basename
                "\$type" => "x-$ext",                    # e.g. "deb", "rpm" or "x-src"
                "\$dist" => "app/$R/$dir",               # e.g. "trusty/main" or "app:pkg:part"
                "\$file" => "http://fossil.include-once.org/$R/cat/$fn",   # resource locator
            ],
            $meta
        );
    }
    return array_values($repo);
}


/**
 * Extract plugin meta data
 * [REGEX]
 *
 *  · really just looks for scalar key:value lines
 *  · comment/docs are not extracted
 *
 */
function meta_extract($files) {
    foreach ($files as $fn=>$cnt) {
        preg_match_all("~\s*(?:#|//|[*])\s*(\w+):\h*(.+)~m", $cnt, $fields);
        $meta = array_combine($fields[1], $fields[2]);
        $meta = array_change_key_case($meta);
        $files[$fn] = $meta;
    }
    return $files;
}



