import madge from "madge";
import fs from "fs";

async function buildDag() {
  console.log("Analyzing import graph...");

  try {
    const res = await madge("src", {
      tsConfig: "tsconfig.json",
      fileExtensions: ["ts", "tsx", "js", "jsx"],
      includeNpm: false,
    });

    const circular = res.circular();

    if (circular.length > 0) {
      console.error("❌ Circular dependencies detected:");
      circular.forEach((cycle) => {
        console.error(`  ${cycle.join(" → ")}`);
      });
      process.exit(1);
    }

    const graph = res.obj();

    fs.writeFileSync("import-dag.json", JSON.stringify(graph, null, 2));

    const nodeCount = Object.keys(graph).length;
    console.log(`✅ Import DAG compiled: ${nodeCount} files`);

  } catch (error) {
    console.error("❌ DAG compilation failed:", error.message);
    process.exit(1);
  }
}

buildDag();
