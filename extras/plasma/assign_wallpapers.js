// Plasma desktop script assigning one wallpaper per activity

const IMAGE_PLUGIN = "org.kde.image";

// Requested wallpapers by activity name (apply.py prepends wallpaperByActivity)
const wallpapers = new Map(Object.entries(wallpaperByActivity));
const unmatchedNames = new Set(wallpapers.keys());
const report = [];

for (const activity of activities()) {
    // Skip unassigned activities
    const name = activityName(activity);
    if (!wallpapers.has(name)) {
        continue;
    }

    // Mark name as matched
    const image = wallpapers.get(name);
    unmatchedNames.delete(name);

    // Set image on every screen of this activity
    for (const desktop of desktopsForActivity(activity)) {
        desktop.wallpaperPlugin = IMAGE_PLUGIN;
        desktop.currentConfigGroup = ["Wallpaper", IMAGE_PLUGIN, "General"];
        desktop.writeConfig("Image", image);

        // Report file name per desktop (regex drops folder path)
        report.push(`${name} desktop ${desktop.id} -> ${image.replace(/^.*\//, "")}`);
    }
}

// Report unmatched names
for (const name of unmatchedNames) {
    report.push(`no activity named ${name}`);
}

// Print report
print(report.join("\n"));
