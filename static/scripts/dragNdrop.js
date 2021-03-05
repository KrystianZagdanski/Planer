function allowDrop(e)
{
    e.preventDefault();
}

function drag(e)
{
    e.dataTransfer.setData("text", e.target.id);
}

function drop(e)
{
    e.preventDefault();
    let id = e.dataTransfer.getData("text");
    if(e.currentTarget.contains(document.getElementById(id)))
        return;
    // id.slice(4) removes 'task' form id
    window.location.replace("/move/"+id.slice(4)+"/"+e.currentTarget.id);
}