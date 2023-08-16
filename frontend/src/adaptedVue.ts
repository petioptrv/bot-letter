import {Vue} from "vue-property-decorator";
import {AdaptedRouter} from "@/router";

export class AdaptedVue extends Vue {
    public $router!: AdaptedRouter;
}