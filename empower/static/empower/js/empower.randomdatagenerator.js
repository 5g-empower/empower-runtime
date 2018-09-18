class EmpRandomDataGenerator{

    constructor(){

        this.data = [];
        this.MAX_LENGTH = 250;

    }

    create(){
         for(var i=0; i<this.MAX_LENGTH; i++){
            this.data.push({"x":Date.now(), "y":0});
         }
         this.update();
    }


    update(){

        var num = { "x":Date.now(),"y": this.generateData() };

        this.data.shift();
        this.data.push(num);

        setTimeout( this.update.bind(this), 1000);
    }

    getData(num){ return this.data.slice(this.MAX_LENGTH-num-1, this.MAX_LENGTH-1); }
    getElement(index = 0){ return this.data[index]; }
    generateData(){ return Math.random(); }

}